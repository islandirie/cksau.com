function createMenu() {
    const menuHTML = `<div class="top-menu" id="top-menu"><ul>
    <li><a href="index.html"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><rect width="100%" height="100%" rx="4" ry="4"></rect></svg></a></li>
    <li><a href="play.html"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><polygon points="12 2 2 22 22 22"></polygon></svg></a></li>
    <li><a href="resume.html"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle></svg></a></li>
    </ul></div>`;

    // Insert the HTML as the first child of the body element
    document.body.insertAdjacentHTML('afterbegin', menuHTML);
}